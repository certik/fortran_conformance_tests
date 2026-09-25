! rule: C1303
! covers: unlimited-item-with-data-descriptor
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_unlimited_item_with_data_descriptor
  implicit none
  integer :: checks
  character(len=3) :: buf
  checks = 0
  buf = '###'
  write(buf,'(SS,*(I1))') 7,8,9
  if (len(buf) /= 3) then
    write(*,'(a)') 'F132134:unlimited_item_with_data_descriptor:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '789') then
    write(*,'(a)') 'F132134:unlimited_item_with_data_descriptor:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:unlimited_item_with_data_descriptor:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 UNLIMITED_ITEM_WITH_DATA_DESCRIPTOR OK'
end program f132134_unlimited_item_with_data_descriptor
