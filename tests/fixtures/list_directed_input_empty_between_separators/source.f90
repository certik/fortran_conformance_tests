! rule: S13.10.3.2-001
! covers: empty-between-separators
! Oracle values are hand-derived from Fortran 2023 13.10.2, 13.10.3.1, or 13.10.3.2.
program list_directed_input_empty_between_separators
  implicit none
  integer :: checks, stray
  character(len=6) :: rec
  integer :: x(3)
  checks=0
  stray=-909
  x=[111,222,333]
  rec = "10,,30"
  read(rec,*) x
  if (x(1) /= 10) then
    write(*,'(a)') 'LDI:empty_between_separators:x1'
    error stop
  end if
  checks=checks+1
  if (x(2) /= 222) then
    write(*,'(a)') 'LDI:empty_between_separators:x2'
    error stop
  end if
  checks=checks+1
  if (x(3) /= 30) then
    write(*,'(a)') 'LDI:empty_between_separators:x3'
    error stop
  end if
  checks=checks+1
  if (checks /= 3) then
    write(*,'(a)') 'LDI:empty_between_separators:check-total'
    error stop
  end if
  write(*,'(a)') 'LIST DIRECTED INPUT EMPTY BETWEEN SEPARATORS OK'
end program list_directed_input_empty_between_separators
