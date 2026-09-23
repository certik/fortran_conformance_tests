program main
  implicit none
  character(len=4) :: base, short*2, wide*6, zero*0
  if (len(base) /= 4) error stop
  if (len(short) /= 2) error stop
  if (len(wide) /= 6) error stop
  if (len(zero) /= 0) error stop
  base = 'wxyz'
  short = 'uv'
  wide = 'abcdef'
  if (base /= 'wxyz') error stop
  if (short /= 'uv') error stop
  if (wide /= 'abcdef') error stop
  print '(a)', 'type_declaration s001 character lengths ok'
end program main
