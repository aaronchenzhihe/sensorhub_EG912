# 优化测试脚本 Ewan.Liu 2025.01.15
import net
import sim
from sim import vsim

def process():
    vsim.getVersion()
    vsim.getProfilesInfo()
    vsim.queryState()
    vsim.enable()
    vsim.selectProfileBySlot(1)
    vsim.selectProfileByIccid('89320420000015083171')
    vsim.queryState()
    vsim.queryCurrentProfile()
    vsim.disable()
    vsim.queryState()
    vsim.queryCurrentProfile()


def main():
    process()

if __name__ == '__main__':
    main()
