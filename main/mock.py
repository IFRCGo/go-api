from unittest.mock import Mock


def erp_request_side_effect_mock(url, json, headers):
    def _generate_mock(status_code, json, headers):
        response_mock = Mock()
        response_mock.text = 'FindThisGUID'
        response_mock.status_code = status_code
        response_mock.json.return_value = json
        return response_mock

    if json['Emergency']['FieldReport']['AffectedCountries']:
        return _generate_mock(200, None, None)
    return _generate_mock(400, None, None)
