subroutine team_spellings(team)
  use iso_fortran_env, only: team_type
  implicit none
  type(team_type), intent(in) :: team
  change team(team)
  endteam
  change team(team)
  end team
end subroutine
