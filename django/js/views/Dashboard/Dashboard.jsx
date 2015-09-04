var React = require('react');

class Dashboard extends React.Component {
    render() {
        return (
            <div>
                Dashboard View Example {this.props.name}
            </div>
        );
    }
}

module.exports = Dashboard;
