! rule: S13.10.3.2-002
! covers: null-preserves-value
! Oracle values are hand-derived from Fortran 2023 13.10.2, 13.10.3.1, or 13.10.3.2.
program list_directed_input_null_preserves_value
  implicit none
  integer :: checks, stray
  character(len=3) :: rec
  integer :: x, y
  checks=0
  stray=-909
  x=717
  y=818
  rec = ",44"
  read(rec,*) x, y
  if (x /= 717) then
    write(*,'(a)') 'LDI:null_preserves_value:x-preserved'
    error stop
  end if
  checks=checks+1
  if (y /= 44) then
    write(*,'(a)') 'LDI:null_preserves_value:y-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'LDI:null_preserves_value:check-total'
    error stop
  end if
  write(*,'(a)') 'LIST DIRECTED INPUT NULL PRESERVES VALUE OK'
end program list_directed_input_null_preserves_value
