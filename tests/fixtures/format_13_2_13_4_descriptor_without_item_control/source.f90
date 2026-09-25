! rule: S13.4-001
! covers: descriptor-without-item-control
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_descriptor_without_item_control
  implicit none
  integer :: checks
  character(len=1) :: buf
  checks = 0
  buf = '#'
  write(buf,'("A")')
  if (len(buf) /= 1) then
    write(*,'(a)') 'F132134:descriptor_without_item_control:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= 'A') then
    write(*,'(a)') 'F132134:descriptor_without_item_control:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:descriptor_without_item_control:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 DESCRIPTOR_WITHOUT_ITEM_CONTROL OK'
end program f132134_descriptor_without_item_control
