! rule: S13.10.3.1-002
! covers: repeat-literal-otherwise
! Oracle values are hand-derived from Fortran 2023 13.10.2, 13.10.3.1, or 13.10.3.2.
program list_directed_input_repeat_literal_otherwise
  implicit none
  integer :: checks, stray
  character(len=8) :: rec
  integer :: x(4)
  checks=0
  stray=-909
  x=[501,502,503,504]
  rec = "5,2*7,19"
  read(rec,*) x
  if (x(1) /= 5) then
    write(*,'(a)') 'LDI:repeat_literal_otherwise:x1'
    error stop
  end if
  checks=checks+1
  if (x(2) /= 7) then
    write(*,'(a)') 'LDI:repeat_literal_otherwise:x2'
    error stop
  end if
  checks=checks+1
  if (x(3) /= 7) then
    write(*,'(a)') 'LDI:repeat_literal_otherwise:x3'
    error stop
  end if
  checks=checks+1
  if (x(4) /= 19) then
    write(*,'(a)') 'LDI:repeat_literal_otherwise:x4'
    error stop
  end if
  checks=checks+1
  if (checks /= 4) then
    write(*,'(a)') 'LDI:repeat_literal_otherwise:check-total'
    error stop
  end if
  write(*,'(a)') 'LIST DIRECTED INPUT REPEAT LITERAL OTHERWISE OK'
end program list_directed_input_repeat_literal_otherwise
