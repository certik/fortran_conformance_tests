! rule: R1304
! covers: nested-format-items-item
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_nested_format_items_item
  implicit none
  integer :: checks
  character(len=4) :: buf
  checks = 0
  buf = '####'
  write(buf,'(SS,2(I1,","))') 3,4
  if (len(buf) /= 4) then
    write(*,'(a)') 'F132134:nested_format_items_item:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '3,4,') then
    write(*,'(a)') 'F132134:nested_format_items_item:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:nested_format_items_item:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 NESTED_FORMAT_ITEMS_ITEM OK'
end program f132134_nested_format_items_item
