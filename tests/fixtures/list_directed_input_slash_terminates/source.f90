! rule: S13.10.3.2-003
! covers: slash-terminates
! Oracle values are hand-derived from Fortran 2023 13.10.2, 13.10.3.1, or 13.10.3.2.
program list_directed_input_slash_terminates
  implicit none
  integer :: checks, stray
  character(len=6) :: rec
  integer :: x, y
  checks=0
  stray=-909
  x=-701
  y=-802
  rec = "1 / 99"
  read(rec,*) x, y
  if (x /= 1) then
    write(*,'(a)') 'LDI:slash_terminates:x-value'
    error stop
  end if
  checks=checks+1
  if (y /= -802) then
    write(*,'(a)') 'LDI:slash_terminates:y-sentinel'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'LDI:slash_terminates:check-total'
    error stop
  end if
  write(*,'(a)') 'LIST DIRECTED INPUT SLASH TERMINATES OK'
end program list_directed_input_slash_terminates
