! rule: R1301
! covers: format-keyword-with-specification
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_format_stmt_keyword_spec
  implicit none
  integer :: checks
  character(len=3) :: buf
  checks = 0
  buf = '###'
100 format(SS,I3)
  write(buf,100) 7
  if (len(buf) /= 3) then
    write(*,'(a)') 'F132134:format_stmt_keyword_spec:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '  7') then
    write(*,'(a)') 'F132134:format_stmt_keyword_spec:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:format_stmt_keyword_spec:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 FORMAT_STMT_KEYWORD_SPEC OK'
end program f132134_format_stmt_keyword_spec
