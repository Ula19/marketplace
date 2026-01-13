from rest_framework.versioning import BaseVersioning


class HeaderVersioning(BaseVersioning):
    version_param = 'version'
    default_version = '1.0'

    def determine_version(self, request, *args, **kwargs):
        header_version = request.headers.get('X-API-Version')
        if header_version:
            return header_version

        accept_header = request.headers.get('Accept')
        if accept_header and 'version=' in accept_header:
            accept_version = accept_header.split('version=')[1].split(';')[0]
            return accept_version

        return self.default_version


class QueryParameterVersioning(BaseVersioning):
    version_param = 'version'  # Параметр, в котором передается версия (может быть 'v' или любой другой)
    default_version = '1'

    def determine_version(self, request, *args, **kwargs):
        version = request.query_params.get(self.version_param)
        if version:
            return version
        return self.default_version
