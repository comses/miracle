module Api.DataColumn exposing (..)

import Http
import Task

import Api.Common
import Raw
import Csrf


setTask: Raw.Column -> Task.Task Http.RawError Http.Response
setTask column =
    let url = "https://localhost/data-column/" ++ toString column.id ++ "/"
        body = Raw.columnToBody column
    in Api.Common.setTask body url