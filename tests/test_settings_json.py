def test_common_keys_exists(settings_json):
    assert isinstance(settings_json['common']['ignoredNodes']['normal'], list)
    assert isinstance(settings_json['common']['ignoredNodes']['advanced'], list)
    assert isinstance(settings_json['common']['ignoredNodes']['normal'], list) 
    assert isinstance(settings_json['common']['generalSettings'], dict) 

def test_misc_keys(settings_json):
    assert isinstance(settings_json["misc"]['labberDelimiter'], str)
    assert isinstance(settings_json["misc"]['ziModules'], list)

def test_common_mapping(settings_json):
    for v in settings_json['common']['quants'].values():
        if "mapping" in v.keys():
            assert "indexes" not in v.keys()
            for k in v["mapping"].values():
                assert "path" in k.keys()
                assert "indexes" in k.keys()
