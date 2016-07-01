module Api.Common exposing (..)

import Http
import Task

import Csrf


getTask: String -> Task.Task Http.RawError Http.Response
getTask url =
  let headers = [ ("Content-Type", "application/json")]
  in Http.send Http.defaultSettings
    { verb = "GET"
    , headers = headers
    , url = url
    , body = Http.empty
    }


setTask: Http.Body -> String -> Task.Task Http.RawError Http.Response
setTask body url =
    let
        -- prepending or appending csrftoken here instead of manually defining headers
        -- produces an run time error "TypeError: xs is undefined".
        headers =
            [ ("Accept", "application/json, text/javascript, */*; q=0.01")
            , ("Content-Type", "application/json; charset=utf-8")
            , ("X-CSRFToken", Csrf.getCsrfToken)
            , ("X-Requested-With", "XMLHttpRequest")
            ]
    in Http.send Http.defaultSettings
        { verb = "PUT"
        , headers = headers
        , url = url
        , body = body
        }