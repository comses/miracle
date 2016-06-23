module Metadata exposing (Model, Msg, update, view, init)

import Html exposing (..)
import Html.App as App
import Html.Attributes exposing (class, type', value)
import Html.Events exposing (onClick)
import Http
import Task
import Debug

import DataTableGroup
import DataColumn as Column
import Raw as R


getDataTableGroup: Task.Task Http.RawError Http.Response
getDataTableGroup =
  let url = "https://localhost/data-group/1.json"
  in Http.send Http.defaultSettings
    { verb = "GET"
    , headers = [ ("Content-Type", "application/json") ]
    , url = url
    , body = Http.empty
    }


getDataTableGroupCmd: Cmd Msg
getDataTableGroupCmd =
    Task.perform FetchFail FetchSucceed
        (getDataTableGroup |> (Http.fromJson R.datatablegroupDecoder))


type alias Model =
    { current: DataTableGroup.Model
    , old: DataTableGroup.Model
    , warning: String }


type Msg 
    = Current DataTableGroup.Msg
    | Cancel
    | Get
    | FetchSucceed R.DataTableGroup
    | FetchFail Http.Error


update: Msg -> Model -> (Model, Cmd Msg)
update msg model = 
    case msg of
        Current msg' -> ({ model | current = DataTableGroup.update msg' model.current }, Cmd.none)

        Cancel -> ({ model | current = model.old }, Cmd.none)

        Get -> (model, getDataTableGroupCmd)

        FetchFail error -> ({ model | warning = toString error }, Cmd.none)

        FetchSucceed current_datatablegroup ->
            let _ = Debug.log "DataTableGroup" current_datatablegroup
                current = DataTableGroup.fromDataTableGroup current_datatablegroup
            in ({model | current = current
                       , old = current}, Cmd.none)


view: Model -> Html Msg
view model =
    let contents =
            [ h1 [] [ text "Metadata" ]
            , App.map Current (DataTableGroup.view model.current)
            , input [ type' "button", value "Save"] []
            , input [ type' "button", onClick Cancel, value "Cancel"] []
            ]
        contents_with_warning = if model.warning /= "" then
            contents ++ [ text model.warning ]
            else contents
    in

    div [ class "container"] contents_with_warning


init: (Model, Cmd Msg)
init = ({ current=DataTableGroup.init, old=DataTableGroup.init, warning="" }, getDataTableGroupCmd)


main = App.program { init = init, view = view, update = update, subscriptions = \_ -> Sub.none }