#!/bin/sh

dscl . create /Users/miracle
dscl . create /Users/miracle RealName "Miracle Docker Account"
dscl . create /Users/miracle hint "Some password hint"
dscl . passwd /Users/miracle thisisanaccountpasswordforthemiracleuser
dscl . create /Users/miracle UniqueID 2000
dscl . create /Users/miracle PrimaryGroupID 2000
dscl . create /Users/miracle UserShell /bin/bash
dscl . create /Users/miracle NFSHomeDirectory /Users/miracle
cp -R /System/Library/User\ Template/English.lproj /Users/miracle

dscl . create /Groups/miracle
dscl . create /Groups/miracle RealName "Miracle Group"
dscl . create /Groups/miracle passwd "*"
dscl . create /Groups/miracle gid 2000
dscl . create /Groups/miracle GroupMembership miracle
dscl . create /Groups/miracle GroupMembership $USER
dscl . append /Groups/miracle GroupMembership miracle

chown -R miracle: /Users/miracle
