"""Decision-path examples only. No claim of semantic or empirical validation."""
def band(*,evaluable=True,unknown=False,usable=False,fragment=False,structural=False,local=False):
    if not evaluable or unknown:return None
    if not usable:return 1
    if not fragment:return 2
    if structural:return 3
    if local:return 4
    return 5
cases=[
('只有页面框架，M3不可评价',dict(evaluable=False),None),
('相关正文可评但无可用内容',{},1),
('仅方向，未形成关键片段',dict(usable=True),2),
('有关键片段，缺完整路径',dict(usable=True,fragment=True,structural=True),3),
('无辅助要求；路径完整但有局部缺口',dict(usable=True,fragment=True,local=True),4),
('全部要求完整，未见实质缺口',dict(usable=True,fragment=True),5),
('局部缺口和结构缺口并存，取结构缺口档',dict(usable=True,fragment=True,local=True,structural=True),3),
('证据未知会影响档位',dict(unknown=True,usable=True),None)]
if __name__=='__main__':
    for name,kw,want in cases:assert band(**kw)==want,name
    print('8个判定路径示例通过；仅核对分档逻辑，不代表真实内容已评完。')
