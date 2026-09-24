program expr_l4_relational_layers
  implicit none
  integer :: checks, x, y
  logical :: ok
  checks = 0
  x = 4
  if (x /= 4) error stop 'L4:level3-base'
  checks = checks + 1
  ok = 2 < 3
  if (.not. ok) error stop 'L4:single-relation-layer'
  checks = checks + 1
  y = 5
  if (y /= 5) error stop 'L4:r1013-single-level3'
  checks = checks + 1
  ok = 3 <= 4
  if (.not. ok) error stop 'L4:r1013-relational-operation'
  checks = checks + 1
  if (len('A') /= 1) error stop 'L4:dot-eq-left-len'
  if (len('A ') /= 2) error stop 'L4:dot-eq-right-len'
  ok = 'A' .EQ. 'A '
  if (.not. ok) error stop 'L4:dot-eq'
  checks = checks + 1
  ok = 4 .NE. 5
  if (.not. ok) error stop 'L4:dot-ne'
  checks = checks + 1
  ok = 3 .LT. 4
  if (.not. ok) error stop 'L4:dot-lt'
  checks = checks + 1
  ok = 4 .LE. 4
  if (.not. ok) error stop 'L4:dot-le'
  checks = checks + 1
  ok = 5 .GT. 4
  if (.not. ok) error stop 'L4:dot-gt'
  checks = checks + 1
  ok = 5 .GE. 5
  if (.not. ok) error stop 'L4:dot-ge'
  checks = checks + 1
  if (len('B') /= 1) error stop 'L4:eqeq-left-len'
  if (len('B ') /= 2) error stop 'L4:eqeq-right-len'
  ok = 'B' == 'B '
  if (.not. ok) error stop 'L4:eqeq'
  checks = checks + 1
  ok = 6 /= 7
  if (.not. ok) error stop 'L4:slash-eq'
  checks = checks + 1
  ok = 1 < 2
  if (.not. ok) error stop 'L4:lt'
  checks = checks + 1
  ok = 2 <= 2
  if (.not. ok) error stop 'L4:le'
  checks = checks + 1
  ok = 3 > 2
  if (.not. ok) error stop 'L4:gt'
  checks = checks + 1
  ok = 3 >= 3
  if (.not. ok) error stop 'L4:ge'
  checks = checks + 1
  if (checks /= 16) error stop 'L4:checks'
  write(*,'(a)') 'EXPRESSIONS LEVEL 4 RELATIONAL OK'
end program expr_l4_relational_layers
