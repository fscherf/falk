from falk.components import HTML5Base


def Index(request, HTML5Base=HTML5Base):
    return """
        <HTML5Base title="Django 5.2 Index" body_id="index">
            <h1>Django 5.2 Test App</h1>

            <ul class="menu">
                <li><a href="/admin/">Django Admin</a></li>
                <li><a href="/admin/login/?next=/">Login</a></li>
                <li><a href="/admin/logout/">Logout</a></li>
                <li><a href="/auth/">Auth</a></li>
                <li><a href="/forms/">Forms</a></li>
            </ul>
        </HTML5Base>
    """
