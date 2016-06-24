module Metadata exposing (Model, Msg, update, view, init)

import Html exposing (..)
import Html.App as App
import Html.Attributes exposing (class, type', value)
import Html.Events exposing (onClick)
import Http
import Task
import Debug
import Json.Encode as Encode

import DataTableGroup
import DataColumn as Column
import Raw as R


getDataTableGroup: Int -> Task.Task Http.RawError Http.Response
getDataTableGroup id =
  let url = "https://localhost/data-group/" ++ toString id ++ ".json"
      headers = [ ("Content-Type", "application/json")]
  in Http.send Http.defaultSettings
    { verb = "GET"
    , headers = headers
    , url = url
    , body = Http.empty
    } `Task.andThen` (\res -> let _ = Debug.log "Headers" res.headers in Task.succeed res)


getDataTableGroupCmd: Int -> Cmd Msg
getDataTableGroupCmd id =
    Task.perform FetchFail FetchSucceed
        (getDataTableGroup id |> (Http.fromJson R.datatablegroupDecoder))


setDataTableGroup: Model -> Task.Task Http.RawError Http.Response
setDataTableGroup model =
    let datatablegroup = DataTableGroup.toDataTableGroup model.current
        -- prepending or appending csrftoken here instead of manually defining headers
        -- produces an run time error "TypeError: xs is undefined".
        headers =
            [ ("Accept", "application/json, text/javascript, */*; q=0.01")
            , ("Content-Type", "application/json; charset=utf-8")
            , ("X-CSRFToken", model.csrftoken)
            , ("X-Requested-With", "XMLHttpRequest")
            ]
        url = "https://localhost/data-group/" ++ toString datatablegroup.id ++ "/"
    in Http.send Http.defaultSettings
        { verb = "PUT"
        , headers = headers
        , url = url
        , body = Http.string (Encode.encode 0 (R.datatablegroupEncoder datatablegroup))
        }


setDataTableGroupCmd: Model -> Cmd Msg
setDataTableGroupCmd model =
    Task.perform FetchFail FetchSucceed
        (setDataTableGroup model |> (Http.fromJson R.datatablegroupDecoder))


type alias Model =
    { current: DataTableGroup.Model
    , old: DataTableGroup.Model
    , warning: String
    , csrftoken: String
    , loading: Bool
    }


type Msg 
    = Current DataTableGroup.Msg
    | Cancel
    | Get Int
    | Set
    | FetchSucceed R.DataTableGroup
    | FetchFail Http.Error


update: Msg -> Model -> (Model, Cmd Msg)
update msg model = 
    case msg of
        Current msg' -> ({ model | current = DataTableGroup.update msg' model.current }, Cmd.none)

        Cancel -> ({ model | current = model.old }, Cmd.none)

        Get id -> (model, getDataTableGroupCmd id)

        Set -> let _ = Debug.log "CSRFToken: " model.csrftoken
                   _ = Debug.log "Current: " model.current
                   datatablegroup = DataTableGroup.toDataTableGroup model.current
                   _ = Debug.log "Set: " datatablegroup
               in (model, setDataTableGroupCmd model)

        FetchFail error -> ({ model | warning = toString error }, Cmd.none)

        FetchSucceed current_datatablegroup ->
            let _ = Debug.log "FetchSucceeded" current_datatablegroup
                current = DataTableGroup.fromDataTableGroup current_datatablegroup
            in ({model | current = current
                       , old = current
                       , loading = False}, Cmd.none)


view: Model -> Html Msg
view model =
    let contents = if model.loading then [ text "Loading" ]
            else [ h1 [] [ text "Metadata" ]
            , App.map Current (DataTableGroup.view model.current)
            , input [ type' "button", onClick Set, value "Save"] []
            , input [ type' "button", onClick Cancel, value "Cancel"] []
            ]
        contents_with_warning = if model.warning /= "" then
            contents ++ [ text model.warning ]
            else contents
    in

    div [ class "container"] contents_with_warning


init: {id: Int, csrftoken: String} -> (Model, Cmd Msg)
init {id, csrftoken} = let model =
                { current=DataTableGroup.init
                , old=DataTableGroup.init
                , warning=""
                , csrftoken=csrftoken
                , loading=True
                }
            in (model, getDataTableGroupCmd id)


main = App.programWithFlags { init = init, view = view, update = update, subscriptions = \_ -> Sub.none }