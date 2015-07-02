{% load static %}
<script src='//cdnjs.cloudflare.com/ajax/libs/knockout/3.3.0/knockout-min.js'></script>
<script src='//cdnjs.cloudflare.com/ajax/libs/knockout.mapping/2.4.1/knockout.mapping.min.js'></script>
<script>
/* 
from http://stackoverflow.com/questions/22706765/twitter-bootstrap-3-modal-with-knockout 
could also use https://github.com/billpull/knockout-bootstrap or 
http://faulknercs.github.io/Knockstrap/
*/

ko.bindingHandlers.modal = {
    init: function (element, valueAccessor) {
        $(element).modal({show: false});
        var value = valueAccessor();
        if (ko.isObservable(value)) {
            $(element).on('hide.bs.modal', function() {
                value(false);
            });
        }
        ko.utils.domNodeDisposal.addDisposeCallback(element, function () {
            $(element).modal("destroy");
        });
    },
    update: function (element, valueAccessor) {
        var value = valueAccessor();
        var unwrappedValue = ko.unwrap(value);
        if (unwrappedValue) {
            $(element).modal('show');
            // focus input field inside dialog
            $("input:first", element).focus();
            $('.has-popover', element).popover({'trigger':'hover'});
        }
        else {
            $(element).modal('hide');
        }
    }
};
</script>
