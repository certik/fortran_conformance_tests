program expr_level5_logical_layers
  implicit none
  integer :: checks
  logical :: ok
  checks = 0
  ok = 2 < 3
  if (.not. ok) error stop 'L5:s-level4-base'
  checks = checks + 1
  ok = .not. false_a()
  if (.not. ok) error stop 'L5:s-not-layer'
  checks = checks + 1
  ok = true_a() .and. false_a()
  if (ok) error stop 'L5:s-and-layer'
  checks = checks + 1
  ok = true_a() .or. false_a() .and. false_b()
  if (.not. ok) error stop 'L5:s-or-layer'
  checks = checks + 1
  ok = true_a() .or. false_a() .eqv. false_b()
  if (ok) error stop 'L5:s-equivalence-layer'
  checks = checks + 1
  ok = 4 == 4
  if (.not. ok) error stop 'R1015:level4-only'
  checks = checks + 1
  ok = .not. (5 == 6)
  if (.not. ok) error stop 'R1015:not-level4'
  checks = checks + 1
  ok = .not. false_b()
  if (.not. ok) error stop 'R1016:single-and-operand'
  checks = checks + 1
  ok = true_a() .and. true_b() .and. false_a()
  if (ok) error stop 'R1016:and-chain'
  checks = checks + 1
  ok = true_a() .and. true_b()
  if (.not. ok) error stop 'R1017:single-or-operand'
  checks = checks + 1
  ok = false_a() .or. true_b()
  if (.not. ok) error stop 'R1017:or-chain'
  checks = checks + 1
  ok = true_b() .or. false_a() .and. false_b()
  if (.not. ok) error stop 'R1017:and-before-or'
  checks = checks + 1
  ok = false_b() .or. true_a()
  if (.not. ok) error stop 'R1018:single-equiv-operand'
  checks = checks + 1
  ok = true_a() .eqv. true_b()
  if (.not. ok) error stop 'R1018:eqv-chain'
  checks = checks + 1
  ok = true_a() .neqv. false_a()
  if (.not. ok) error stop 'R1018:neqv-chain'
  checks = checks + 1
  ok = .not. false_a()
  if (.not. ok) error stop 'R1019:dot-not-token'
  checks = checks + 1
  ok = true_a() .and. false_b()
  if (ok) error stop 'R1020:dot-and-token'
  checks = checks + 1
  ok = false_a() .or. true_a()
  if (.not. ok) error stop 'R1021:dot-or-token'
  checks = checks + 1
  ok = true_b() .eqv. true_a()
  if (.not. ok) error stop 'R1022:dot-eqv-token'
  checks = checks + 1
  ok = true_b() .neqv. false_b()
  if (.not. ok) error stop 'R1022:dot-neqv-token'
  checks = checks + 1
  if (checks /= 20) error stop 'L5:checks'
  write(*,'(a)') 'EXPRESSIONS LEVEL 5 LOGICAL OK'
contains
  pure logical function true_a()
    true_a = .true.
  end function true_a
  pure logical function true_b()
    true_b = .true.
  end function true_b
  pure logical function false_a()
    false_a = .false.
  end function false_a
  pure logical function false_b()
    false_b = .false.
  end function false_b
end program expr_level5_logical_layers
