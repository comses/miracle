module Api.Analysis exposing (..)

import Http
import Task

import Raw
import Csrf

import Json.Decode as Decode exposing (Decoder)

type alias FromModel model = Raw.Analysis -> model
type alias ToModel model = model -> Raw.Analysis
type alias FetchSuccess model msg = model -> msg
type alias FetchFail msg = Http.Error -> msg

setTask: Raw.Analysis -> Task.Task Http.RawError Http.Response
setTask column =
    let headers =
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


set: model -> ToModel model -> FetchSuccess model msg -> FetchFail msg -> Cmd msg
set model toModel fetchFail fetchSuccess =
    Task.perform
        fetchFail
        fetchSuccess
        (setTask (Debug.log "Column" (toModel model)) |> (Http.fromJson Raw.))