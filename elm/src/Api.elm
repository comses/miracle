module Api exposing (getProjectsForUser, updateProject)

import Http
import Json.Decode as Json exposing ((:=))

import Hop exposing (..)
import Hop.Matchers exposing (match1, match2, int, str)
import Hop.Types exposing (Config, Query, Location, PathMatcher, Router)

import Platform exposing (Task)

import Metadata

-- Routes

type Route
    = DashboardRoute
    | ProjectRoute String
    | ProjectListRoute
    | NotFound


dashboardMatcher : PathMatcher Route
dashboardMatcher =
    match1 DashboardRoute "/dashboard"

projectMatcher : PathMatcher Route
projectMatcher =
    match2 ProjectRoute "/projects/" str

projectListMatcher : PathMatcher Route
projectListMatcher =
    match1 ProjectListRoute "/projects/"

reverse : Route -> String
reverse route =
    case route of

        DashboardRoute ->
            matcherToPath dashboardMatcher []

        ProjectRoute slug ->
            matcherToPath projectMatcher [slug]

        ProjectListRoute ->
            matcherToPath projectListMatcher []

        NotFound -> 
            ""

-- Projects API

getProjectMetadata: String -> Task Http.Error Metadata.Model
getProjectMetadata slug =


getProjectsForUser : Task Http.Error (List String)
getProjectsForUser =
    Http.get projects (reverse ProjectListRoute)

