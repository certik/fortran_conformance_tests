! rule: S13.2.2-004
! covers: array-element-contained-format
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_array_element_contained_format
  implicit none
  integer :: checks
  character(len=7) :: fmt(2)
  character(len=3) :: buf
  checks = 0
  fmt = [character(len=7) :: '(SS,I3)', '(SS,I1)']
  buf = '###'
  write(buf,fmt(1)) 7
  if (len(buf) /= 3) then
    write(*,'(a)') 'F132134:array_element_contained_format:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '  7') then
    write(*,'(a)') 'F132134:array_element_contained_format:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:array_element_contained_format:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 ARRAY_ELEMENT_CONTAINED_FORMAT OK'
end program f132134_array_element_contained_format
