! rule: C1301
! covers: labelled-format-stmt
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_labelled_format_stmt
  implicit none
  integer :: checks
  character(len=2) :: buf
  checks = 0
  buf = '##'
100 format(SS,I2)
200 format(SS,I1)
  write(buf,100) 8
  if (len(buf) /= 2) then
    write(*,'(a)') 'F132134:labelled_format_stmt:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= ' 8') then
    write(*,'(a)') 'F132134:labelled_format_stmt:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:labelled_format_stmt:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 LABELLED_FORMAT_STMT OK'
end program f132134_labelled_format_stmt
