! rule: S13.10.2-002
! covers: repeat-constant
! Oracle values are hand-derived from Fortran 2023 13.10.2, 13.10.3.1, or 13.10.3.2.
program list_directed_input_repeat_constant
  implicit none
  integer :: checks, stray
  character(len=9) :: rec
  integer :: x(5)
  checks=0
  stray=-909
  x=[101,202,303,404,505]
  rec = "11,3*7,29"
  read(rec,*) x
  if (x(1) /= 11) then
    write(*,'(a)') 'LDI:repeat_constant:x1'
    error stop
  end if
  checks=checks+1
  if (x(2) /= 7) then
    write(*,'(a)') 'LDI:repeat_constant:x2'
    error stop
  end if
  checks=checks+1
  if (x(3) /= 7) then
    write(*,'(a)') 'LDI:repeat_constant:x3'
    error stop
  end if
  checks=checks+1
  if (x(4) /= 7) then
    write(*,'(a)') 'LDI:repeat_constant:x4'
    error stop
  end if
  checks=checks+1
  if (x(5) /= 29) then
    write(*,'(a)') 'LDI:repeat_constant:x5'
    error stop
  end if
  checks=checks+1
  if (checks /= 5) then
    write(*,'(a)') 'LDI:repeat_constant:check-total'
    error stop
  end if
  write(*,'(a)') 'LIST DIRECTED INPUT REPEAT CONSTANT OK'
end program list_directed_input_repeat_constant
