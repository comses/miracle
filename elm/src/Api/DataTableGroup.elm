module Api.DataTableGroup exposing (..)

import Http
import Task

import Raw
import Csrf


getTask: Int -> Task.Task Http.RawError Http.Response
getTask id =
  let url = "https://localhost/data-group/" ++ toString id ++ ".json"
      headers = [ ("Content-Type", "application/json")]
  in Http.send Http.defaultSettings
    { verb = "GET"
    , headers = headers
    , url = url
    , body = Http.empty
    } `Task.andThen` (\res -> let _ = Debug.log "Headers" res.headers in Task.succeed res)


setTask: Raw.DataTableGroup -> Task.Task Http.RawError Http.Response
setTask datatablegroup =
    let
        -- prepending or appending csrftoken here instead of manually defining headers
        -- produces an run time error "TypeError: xs is undefined".
        headers =
            [ ("Accept", "application/json, text/javascript, */*; q=0.01")
            , ("Content-Type", "application/json; charset=utf-8")
            , ("X-CSRFToken", Csrf.getCsrfToken)
            , ("X-Requested-With", "XMLHttpRequest")
            ]
        url = "https://localhost/data-group/" ++ toString datatablegroup.id ++ "/"
    in Http.send Http.defaultSettings
        { verb = "PUT"
        , headers = headers
        , url = url
        , body = Raw.datatablegroupBody datatablegroup
        }
