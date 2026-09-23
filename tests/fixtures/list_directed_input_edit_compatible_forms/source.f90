! rule: S13.10.3.1-001
! covers: edit-compatible-forms
! Oracle values are hand-derived from Fortran 2023 13.10.2, 13.10.3.1, or 13.10.3.2.
program list_directed_input_edit_compatible_forms
  implicit none
  integer :: checks, stray
  character(len=6) :: rec_i, rec_l
  integer :: n
  logical :: flag
  checks=0
  stray=-909
  n=-404
  flag=.false.
  rec_i = "42"
  read(rec_i,*) n
  rec_l = ".TRUE."
  read(rec_l,*) flag
  if (n /= 42) then
    write(*,'(a)') 'LDI:edit_compatible_forms:integer-value'
    error stop
  end if
  checks=checks+1
  if (flag .neqv. .true.) then
    write(*,'(a)') 'LDI:edit_compatible_forms:logical-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'LDI:edit_compatible_forms:check-total'
    error stop
  end if
  write(*,'(a)') 'LIST DIRECTED INPUT EDIT COMPATIBLE FORMS OK'
end program list_directed_input_edit_compatible_forms
