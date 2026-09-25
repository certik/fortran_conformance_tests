program io_list_derived_formatted_components
  implicit none
  type :: pair
    integer :: code
    character(len=2) :: tag
  end type pair
  integer :: checks
  type(pair) :: item
  character(len=4) :: rec
  character(len=6) :: out
  checks = 0
  rec = '7 AB'
  item = pair(-8, 'ZZ')
  if (item%code /= -8) error stop 'code pre-read sentinel'
  checks = checks + 1
  if (len(item%tag) /= 2) error stop 'tag len before read'
  checks = checks + 1
  if (item%tag /= 'ZZ') error stop 'tag pre-read sentinel'
  checks = checks + 1
  read(rec,'(I1,1X,A2)') item
  if (item%code /= 7) error stop 'derived read integer component'
  checks = checks + 1
  if (len(item%tag) /= 2) error stop 'tag len after read'
  checks = checks + 1
  if (item%tag /= 'AB') error stop 'derived read character component'
  checks = checks + 1
  item = pair(42, 'QR')
  out = '######'
  write(out,'(SS,I2,A2)') item
  if (out /= '42QR  ') error stop 'derived write component order'
  checks = checks + 1
  if (checks /= 7) error stop 'checks'
  print '(a)', 'IO_LIST_12_6_3 DERIVED_FORMATTED_COMPONENTS OK'
end program io_list_derived_formatted_components
