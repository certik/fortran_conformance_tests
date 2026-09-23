! rule: S13.8.2-004
! covers: slash-explicit-repeat
! Expected characters and numeric values are hand-derived from Fortran 2023 clause 13.
program ced_slash_explicit_repeat
  implicit none
  integer :: checks
  character(len=1) :: rec(3)
  character(len=3) :: observed
  checks=0
  rec = '#'
  write(rec,'("A",2/,"B")')
  observed = rec(1) // rec(2) // rec(3)
  if (observed /= 'A B') then
    write(*,'(a)') 'CED:slash_explicit_repeat:observed-characters'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'CED:slash_explicit_repeat:check-total'
    error stop
  end if
  write(*,'(a)') 'CONTROL EDIT SLASH_EXPLICIT_REPEAT OK'
end program ced_slash_explicit_repeat
