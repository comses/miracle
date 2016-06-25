module Api.DataColumn exposing (..)

import Http
import Task

import Raw
import Csrf

import DataColumn exposing (toColumn)


type Msg
    = Set
    | FetchSucceed Raw.Column
    | FetchFail Http.Error


setTask: DataColumn.Model -> Task.Task Http.RawError Http.Response
setTask model =
    let column = toColumn model
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


set: DataColumn.Model -> Cmd Msg
set model =
    Task.perform
        FetchFail
        FetchSucceed
        (setTask model |> (Http.fromJson Raw.columnDecoder))