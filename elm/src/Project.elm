module Project exposing (..)

import Html exposing (..)
import Html.Attributes exposing (class, style)
import Html.Events
import Html.App as App

import Array
import Date
import Json.Decode

import Http
import Task

import Api.Project
import Analysis
import ArrayComponent
import Cancelable
import DataTableGroup
import Raw


type alias Model =
    { id: Int
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


toRawProject: Model -> Raw.ProjectOutgoing
toRawProject model =
    { id = model.id
    , creator = model.creator
    , published = model.published
    , slug = model.slug
    , description = model.description
    , name = model.name
    }


fromRawProject: Raw.ProjectIncoming -> Model
fromRawProject raw_project =
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
    | ModifyDataTableGroup Int DataTableGroup.Msg
    | ModifyAnalysis Int Analysis.Msg


updateDataTableGroups:
    Int -> DataTableGroup.Msg -> Array.Array DataTableGroup.Model -> (Array.Array DataTableGroup.Model, Cmd Msg)
updateDataTableGroups =
    ArrayComponent.updateChild ModifyDataTableGroup DataTableGroup.update


updateAnalyses:
    Int -> Analysis.Msg -> Array.Array Analysis.Model -> (Array.Array Analysis.Model, Cmd Msg)
updateAnalyses =
    ArrayComponent.updateChild ModifyAnalysis Analysis.update


update: Msg -> Model -> (Model, Cmd Msg)
update msg model =
    case msg of
        Get slug -> (model, get slug)

        FetchSucceed raw_projectincoming -> (fromRawProject raw_projectincoming, Cmd.none)

        FetchFail err ->
                ({ model | warning = err }, Cmd.none)

        ModifyDataTableGroup id datatablegroup_msg ->
            let (datatablegroups, msg') = updateDataTableGroups id datatablegroup_msg model.data_table_groups
            in ({ model | data_table_groups = datatablegroups }, msg')

        ModifyAnalysis id analysis_msg ->
            let (analyses, msg') = updateAnalyses id analysis_msg model.analyses
            in ({ model | analyses = analyses }, msg')


init: String -> (Model, Cmd Msg)
init project_incoming_str =
    let project_incoming_result = Json.Decode.decodeString Raw.projectDecoder project_incoming_str
    in
        case project_incoming_result of
            Ok project_incoming -> (fromRawProject project_incoming, Cmd.none)

            Err message -> Debug.crash message


get: String -> Cmd Msg
get slug =
    Task.perform
        (toString >> FetchFail)
        FetchSucceed
        (Api.Project.getTask slug |> (Http.fromJson Raw.projectDecoder))