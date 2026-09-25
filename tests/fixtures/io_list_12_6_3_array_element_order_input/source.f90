program io_list_array_element_order_input
  implicit none
  integer :: checks
  character(len=7) :: rec
  integer :: a(2,2)
  checks = 0
  rec = '1 2 3 4'
  a = reshape([-11, -22, -33, -44], [2, 2])
  if (any(reshape(a, [4]) /= [-11, -22, -33, -44])) error stop 'a pre-read sentinel'
  checks = checks + 1
  read(rec,*) a
  if (any(reshape(a, [4]) /= [1, 2, 3, 4])) error stop 'array element order'
  checks = checks + 1
  if (checks /= 2) error stop 'checks'
  print '(a)', 'IO_LIST_12_6_3 ARRAY_ELEMENT_ORDER_INPUT OK'
end program io_list_array_element_order_input
