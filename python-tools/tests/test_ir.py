import pytest
from lqp.ir import RelationId, SourceInfo

def test_relation_id_str_no_meta():
    rel_id = RelationId(meta=None, id=12345)
    assert str(rel_id) == "RelationId(id=12345)"

def test_relation_id_str_with_meta():
    source_info = SourceInfo(file="test.lqp", line=1, column=10)
    rel_id = RelationId(meta=source_info, id=67890)
    assert str(rel_id) == "RelationId(meta=test.lqp:1:10, id=67890)"
