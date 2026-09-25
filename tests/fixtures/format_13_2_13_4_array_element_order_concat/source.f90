! rule: S13.2.2-003
! covers: array-element-order-concatenation
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_array_element_order_concat
  implicit none
  integer :: checks
  character(len=4) :: fmt(4)
  character(len=3) :: buf
  checks = 0
  fmt = [character(len=4) :: '(SS', ',I1', ',I1', ')   ']
  buf = '###'
  write(buf,fmt) 2,5
  if (len(buf) /= 3) then
    write(*,'(a)') 'F132134:array_element_order_concat:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '25 ') then
    write(*,'(a)') 'F132134:array_element_order_concat:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:array_element_order_concat:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 ARRAY_ELEMENT_ORDER_CONCAT OK'
end program f132134_array_element_order_concat
