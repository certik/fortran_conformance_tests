! rule: R1305
! covers: asterisk-parenthesized-list
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_asterisk_parenthesized_list
  implicit none
  integer :: checks
  character(len=5) :: buf
  checks = 0
  buf = '#####'
  write(buf,'(SS,*(I1,:,";"))') 4,5,6
  if (len(buf) /= 5) then
    write(*,'(a)') 'F132134:asterisk_parenthesized_list:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '4;5;6') then
    write(*,'(a)') 'F132134:asterisk_parenthesized_list:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:asterisk_parenthesized_list:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 ASTERISK_PARENTHESIZED_LIST OK'
end program f132134_asterisk_parenthesized_list
