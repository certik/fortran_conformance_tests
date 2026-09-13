! rule: S10.2.1.3-023
! covers: same-image-control
! evidence: context-only
! requires: coarray
! F2023 10.2.1.3 p14: same-image TEAM_TYPE control only.
program s10_2_1_3_023_team
    use iso_fortran_env, only: team_type
    implicit none
    type(team_type) :: source, copy
    form team (1, source)
    copy = source
    change team (copy)
        if (team_number() /= 1) error stop 'same-image-team'
    end team
end program
