module Project exposing (..)

import Html exposing (..)
import Html.Attributes
import Html.Events
import Html.App as App

import Array
import Date

import Http
import Task

import Api.Project
import Analysis
import DataTableGroup
import Raw


type Model =
    Main { id: Int
        , url: String
        , group_members: Array.Array String
        , creator: String
        , published: Bool
        , published_on: Maybe Date.Date
        , date_created: Date.Date
        , number_of_datasets: Int
        , data_table_groups: Array.Array DataTableGroup.Model
        , analyses: Array.Array Analysis.Model
        , slug: String
        , description: String
        , name: String
        , comments: Array.Array String
--        , recent_activity: Array.Array String
        , warning: String
        }
    | Splash { warning: String }


toRawProject: Model -> Result String Raw.ProjectOutgoing
toRawProject model =
    case model of
        Main model' ->
            Ok { id = model'.id
                , creator = model'.creator
                , published = model'.published
                , slug = model'.slug
                , description = model'.description
                , name = model'.name
                }

        _ -> Err ""


fromRawProject: Raw.ProjectIncoming -> Model
fromRawProject raw_project =
    Main
    { id = raw_project.id
    , url = raw_project.url
    , group_members = raw_project.group_members
    , creator = raw_project.creator
    , published = raw_project.published
    , published_on = raw_project.published_on
    , date_created = raw_project.date_created
    , number_of_datasets = raw_project.number_of_datasets
    , data_table_groups = Array.map DataTableGroup.fromRawDataTableGroup raw_project.data_table_groups
    , analyses = Array.map Analysis.fromRawAnalysis raw_project.analyses
    , slug = raw_project.slug
    , description =raw_project.description
    , name = raw_project.name
    , comments = raw_project.comments
--    , recent_activity = raw_project.recent_activity
    , warning = ""
    }


type Msg
    = Get String
    | FetchSucceed Raw.ProjectIncoming
    | FetchFail String


update: Msg -> Model -> (Model, Cmd Msg)
update msg model =
    case msg of
        Get slug -> (model, get slug)

        FetchSucceed raw_projectincoming -> (fromRawProject raw_projectincoming, Cmd.none)

        FetchFail err ->
            case model of
                Main model' -> (Main { model' | warning = err }, Cmd.none)

                Splash model' -> (Splash { model' | warning = err }, Cmd.none)


view: Model -> Html Msg
view model = text (toString model)


init: (Model, Cmd Msg)
init = (Splash { warning = "" }, get "luxedemo")


get: String -> Cmd Msg
get slug =
    Task.perform
        (toString >> FetchFail)
        FetchSucceed
        (Api.Project.getTask slug |> (Http.fromJson Raw.projectDecoder))


main = App.program { init = init, update = update, subscriptions = \_ -> Sub.none, view = view}