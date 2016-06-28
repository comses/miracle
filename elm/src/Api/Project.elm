module Api.Project exposing (..)

import Http
import Task

import Api.Common
import Raw
import Csrf


getTask: String -> Task.Task Http.RawError Http.Response
getTask slug =
    let url = "https://localhost/projects/" ++ slug ++ ".json"
    in Api.Common.getTask url