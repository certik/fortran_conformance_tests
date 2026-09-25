program io_list_basic_input_output
  implicit none
  integer :: checks
  character(len=2) :: rec
  character(len=6) :: out
  integer :: x, spare
  checks = 0
  rec = '17'
  out = '######'
  x = -777
  spare = -333
  if (x /= -777) error stop 'x pre-read sentinel'
  checks = checks + 1
  read(rec,*) x
  if (x /= 17) error stop 'x read value'
  checks = checks + 1
  if (spare /= -333) error stop 'unlisted entity changed'
  checks = checks + 1
  write(out,'(SS,I2)') x + 5
  if (len(out) /= 6) error stop 'out len'
  checks = checks + 1
  if (out /= '22    ') error stop 'output expression value'
  checks = checks + 1
  if (checks /= 5) error stop 'checks'
  print '(a)', 'IO_LIST_12_6_3 BASIC_INPUT_OUTPUT OK'
end program io_list_basic_input_output
