from tethys_sdk.base import TethysAppBase, url_map_maker


class Grace(TethysAppBase):
    """
    Tethys app class for Grace.
    """

    name = 'Grace'
    index = 'grace:home'
    icon = 'grace/images/icon.gif'
    package = 'grace'
    root_url = 'grace'
    color = '#e74c3c'
    description = ''
    tags = ''
    enable_feedback = False
    feedback_emails = []

        
    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (UrlMap(name='home',
                           url='grace',
                           controller='grace.controllers.home'),
                     UrlMap(name='home_graph',
                           url='grace/home/{id}',
                           controller='grace.controllers.home_graph'),
                )

        return url_maps