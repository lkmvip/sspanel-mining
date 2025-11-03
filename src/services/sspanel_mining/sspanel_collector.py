# 放在文件顶部的 import（如果已有就不要重复）
import time
from selenium.webdriver.common.by import By
from services.settings import logger
from services.sspanel_mining.exceptions import CollectorSwitchError  # 仍保留引用，但不会因为无“下一页”而抛

# ================== 替换这个方法 ==================
def _page_tracking(self, api) -> bool:
    """
    翻页逻辑：
      - 优先点击 Google 传统翻页按钮（兼容多种选择器）
      - 若没有“下一页”按钮，尝试一次滚动到底以触发连续加载
      - 若仍无更多内容，返回 False（结束分页），而不是抛异常
    返回:
      True  -> 已成功进入下一页（或加载出更多内容，应继续抓取）
      False -> 没有下一页 / 无更多内容（本轮分页正常结束）
    """
    try:
        # 1) 兼容多版本 SERP 的“下一页”定位
        selectors = [
            (By.CSS_SELECTOR, 'a#pnnext'),                    # 旧式按钮
            (By.CSS_SELECTOR, 'a[aria-label="Next page"]'),   # 新式按钮（英文）
            (By.CSS_SELECTOR, 'a[aria-label="Next"]'),        # 变体
            (By.CSS_SELECTOR, 'a[aria-label="下一页"]'),        # 简体中文界面
            (By.CSS_SELECTOR, 'a[rel="next"]'),               # 通用 rel
        ]

        for by, sel in selectors:
            try:
                next_obj = api.find_element(by, sel)
                # 某些场景需要滚动到可见再点击
                try:
                    api.execute_script("arguments[0].scrollIntoView({block:'center'});", next_obj)
                except Exception:
                    pass
                next_obj.click()
                # 等待下一页加载一点时间（也可用 WebDriverWait 更精细）
                time.sleep(1.2)
                return True
            except Exception:
                continue

        # 2) 兜底：如果是“连续滚动”样式，没有显式下一页按钮
        #    先记录当前结果数量（尽量用更稳的选择器，这里示例常见的卡片容器）
        def _count_results():
            try:
                elems = api.find_elements(By.CSS_SELECTOR, "div.g, div.MjjYud, div[jscontroller]")  # 常见结果容器
                return len(elems)
            except Exception:
                return 0

        before = _count_results()
        try:
            api.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1.5)  # 给懒加载一点时间
        except Exception:
            pass
        after = _count_results()

        if after > before:
            # 有新增内容 -> 视为“翻到下一页”效果，继续抓
            return True

        # 3) 没有下一页也没有新增内容 -> 正常结束分页
        return False

    except Exception as e:
        # 保守处理：不要因无法找到“下一页”而让任务失败
        logger.exception(e)
        return False
# ================== 替换结束 ==================
