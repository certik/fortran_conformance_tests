! rule: S13.10.3.2-003
! covers: slash-null-supplies-remaining
! Oracle values are hand-derived from Fortran 2023 13.10.2, 13.10.3.1, or 13.10.3.2.
program list_directed_input_slash_null_supplies_remaining
  implicit none
  integer :: checks, stray
  character(len=3) :: rec
  integer :: x(3)
  checks=0
  stray=-909
  x=[501,602,703]
  rec = "1 /"
  read(rec,*) x
  if (x(1) /= 1) then
    write(*,'(a)') 'LDI:slash_null_supplies_remaining:x1'
    error stop
  end if
  checks=checks+1
  if (x(2) /= 602) then
    write(*,'(a)') 'LDI:slash_null_supplies_remaining:x2'
    error stop
  end if
  checks=checks+1
  if (x(3) /= 703) then
    write(*,'(a)') 'LDI:slash_null_supplies_remaining:x3'
    error stop
  end if
  checks=checks+1
  if (checks /= 3) then
    write(*,'(a)') 'LDI:slash_null_supplies_remaining:check-total'
    error stop
  end if
  write(*,'(a)') 'LIST DIRECTED INPUT SLASH NULL SUPPLIES REMAINING OK'
end program list_directed_input_slash_null_supplies_remaining
