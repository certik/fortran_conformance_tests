! rule: S13.2.1-001
! covers: embedded-blanks-between-descriptors
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_embedded_blanks_between_descriptors
  implicit none
  integer :: checks
  character(len=5) :: buf
  checks = 0
  buf = '#####'
  write(buf,'( SS , I3 , 1X , I1 )') 7,4
  if (len(buf) /= 5) then
    write(*,'(a)') 'F132134:embedded_blanks_between_descriptors:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '  7 4') then
    write(*,'(a)') 'F132134:embedded_blanks_between_descriptors:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:embedded_blanks_between_descriptors:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 EMBEDDED_BLANKS_BETWEEN_DESCRIPTORS OK'
end program f132134_embedded_blanks_between_descriptors
