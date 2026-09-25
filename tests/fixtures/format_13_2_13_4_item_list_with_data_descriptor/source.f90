! rule: S13.4-002
! covers: item-list-with-data-descriptor
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_item_list_with_data_descriptor
  implicit none
  integer :: checks
  character(len=2) :: buf
  checks = 0
  buf = '##'
  write(buf,'(SS,"A",I1)') 7
  if (len(buf) /= 2) then
    write(*,'(a)') 'F132134:item_list_with_data_descriptor:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= 'A7') then
    write(*,'(a)') 'F132134:item_list_with_data_descriptor:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:item_list_with_data_descriptor:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 ITEM_LIST_WITH_DATA_DESCRIPTOR OK'
end program f132134_item_list_with_data_descriptor
