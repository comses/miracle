module Api.DataColumn exposing (..)

import Http
import Task

import Raw
import Csrf


setTask: Raw.Column -> Task.Task Http.RawError Http.Response
setTask column =
    let
        -- prepending or appending csrftoken here instead of manually defining headers
        -- produces an run time error "TypeError: xs is undefined".
        headers =
            [ ("Accept", "application/json, text/javascript, */*; q=0.01")
            , ("Content-Type", "application/json; charset=utf-8")
            , ("X-CSRFToken", Csrf.getCsrfToken)
            , ("X-Requested-With", "XMLHttpRequest")
            ]
        url = "https://localhost/data-column/" ++ toString column.id ++ "/"
    in Http.send Http.defaultSettings
        { verb = "PUT"
        , headers = headers
        , url = url
        , body = Raw.columnToBody column
        }