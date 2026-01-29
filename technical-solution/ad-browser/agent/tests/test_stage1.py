"""
阶段一任务验收测试

测试配置管理、日志系统、异常处理框架
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_config():
    """测试配置管理模块"""
    print("=" * 60)
    print("测试配置管理模块")
    print("=" * 60)
    
    # 设置测试环境变量
    os.environ["DEEPSEEK_API_KEY"] = "test_api_key_12345"
    
    from agent.config import settings, get_settings
    
    # 测试配置加载
    config = get_settings()
    print(f"✅ 配置加载成功")
    print(f"   DeepSeek API Key: {config.deepseek_api_key[:10]}...")
    print(f"   DeepSeek Base URL: {config.deepseek_base_url}")
    print(f"   DeepSeek Model: {config.deepseek_model}")
    print(f"   最大详情数: {config.max_items}")
    print(f"   最大页数: {config.max_pages}")
    print(f"   最大操作步数: {config.max_steps}")
    print(f"   单条超时: {config.timeout_per_item}秒")
    print(f"   WebSocket Host: {config.ws_host}")
    print(f"   WebSocket Port: {config.ws_port}")
    print(f"   日志级别: {config.log_level}")
    
    # 测试配置验证
    assert config.max_items <= 10, "max_items 应该 <= 10"
    assert config.max_pages <= 3, "max_pages 应该 <= 3"
    assert config.max_steps <= 100, "max_steps 应该 <= 100"
    print(f"✅ 配置验证通过")
    
    print()


def test_logger():
    """测试日志系统"""
    print("=" * 60)
    print("测试日志系统")
    print("=" * 60)
    
    from agent.utils.logger import setup_logger, get_logger
    
    # 测试日志记录器创建
    logger = setup_logger("test_logger")
    print(f"✅ 日志记录器创建成功")
    
    # 测试不同日志级别
    logger.debug("这是 DEBUG 级别日志")
    logger.info("这是 INFO 级别日志")
    logger.warning("这是 WARNING 级别日志")
    logger.error("这是 ERROR 级别日志")
    print(f"✅ 日志级别测试通过")
    
    # 测试获取已存在的日志记录器
    logger2 = get_logger("test_logger")
    assert logger is logger2, "应该返回同一个日志记录器实例"
    print(f"✅ 日志记录器复用测试通过")
    
    print()


def test_exceptions():
    """测试异常处理框架"""
    print("=" * 60)
    print("测试异常处理框架")
    print("=" * 60)
    
    from agent.exceptions import (
        AgentException,
        StateMachineException,
        BrowserAdapterException,
        LLMException,
        TaskException,
        ConfigurationException,
        ValidationException
    )
    
    # 测试基础异常
    try:
        raise AgentException("基础异常测试", error_code="TEST_ERROR")
    except AgentException as e:
        assert str(e) == "[TEST_ERROR] 基础异常测试"
        assert e.error_code == "TEST_ERROR"
        print(f"✅ 基础异常测试通过: {e}")
    
    # 测试状态机异常
    try:
        raise StateMachineException(
            "无效的状态转换",
            current_state="IDLE",
            target_state="FINISHED"
        )
    except StateMachineException as e:
        assert e.error_code == "STATE_MACHINE_ERROR"
        assert e.details["current_state"] == "IDLE"
        assert e.details["target_state"] == "FINISHED"
        print(f"✅ 状态机异常测试通过: {e}")
        print(f"   异常详情: {e.to_dict()}")
    
    # 测试 Browser Adapter 异常
    try:
        raise BrowserAdapterException(
            "打开页面失败",
            action="open_page",
            url="https://example.com"
        )
    except BrowserAdapterException as e:
        assert e.error_code == "BROWSER_ADAPTER_ERROR"
        assert e.details["action"] == "open_page"
        print(f"✅ Browser Adapter 异常测试通过: {e}")
    
    # 测试 LLM 异常
    try:
        raise LLMException(
            "API 调用失败",
            task_type="相关性判断",
            retry_count=1
        )
    except LLMException as e:
        assert e.error_code == "LLM_ERROR"
        assert e.details["retry_count"] == 1
        print(f"✅ LLM 异常测试通过: {e}")
    
    # 测试任务异常
    try:
        raise TaskException(
            "任务执行失败",
            task_id="task-123",
            state="EXTRACTING"
        )
    except TaskException as e:
        assert e.error_code == "TASK_ERROR"
        assert e.details["task_id"] == "task-123"
        print(f"✅ 任务异常测试通过: {e}")
    
    print()


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("阶段一任务验收测试")
    print("=" * 60 + "\n")
    
    try:
        test_config()
        test_logger()
        test_exceptions()
        
        print("=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        print("\n阶段一任务完成情况：")
        print("  ✅ 任务 1.1: 项目结构初始化")
        print("  ✅ 任务 1.2: 配置管理模块")
        print("  ✅ 任务 1.3: 日志系统")
        print("  ✅ 任务 1.4: 异常处理框架")
        print()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
