var React = require('react');

class ProjectDetail {
    render() {
        return (
            <div>
                Project Detail View
            </div>
        );
    }
};
class Dashboard extends React.Component {
    render() {
        return (
            <div>
                Dashboard View Example {this.props.name}
            </div>
        );
    }
}

module.exports = [Dashboard, ProjectDetail];
