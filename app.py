from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


def minimize_dfa(states, alphabet, start, final_states, transitions):

    # -----------------------------
    # Create transition dictionary
    # -----------------------------

    transition = {}

    for state in states:
        transition[state] = {}

    for t in transitions:

        transition[t["from"]][t["symbol"]] = t["to"]


    # -----------------------------
    # Check complete DFA
    # -----------------------------

    for state in states:

        for symbol in alphabet:

            if symbol not in transition[state]:

                raise ValueError(
                    f"Missing transition: {state}, {symbol}"
                )


    # -----------------------------
    # Remove unreachable states
    # -----------------------------

    reachable = set()
    queue = [start]

    reachable.add(start)

    while queue:

        current = queue.pop(0)

        for symbol in alphabet:

            next_state = transition[current][symbol]

            if next_state not in reachable:

                reachable.add(next_state)
                queue.append(next_state)


    reachable_states = [
        state for state in states
        if state in reachable
    ]

    reachable_final = [
        state for state in final_states
        if state in reachable
    ]


    # -----------------------------
    # Initial partition
    # -----------------------------

    final_set = set(reachable_final)

    non_final = [
        state for state in reachable_states
        if state not in final_set
    ]

    partitions = []

    if non_final:
        partitions.append(non_final)

    if reachable_final:
        partitions.append(reachable_final)


    # -----------------------------
    # Partition refinement
    # -----------------------------

    changed = True

    while changed:

        changed = False

        new_partitions = []

        for group in partitions:

            groups = {}

            for state in group:

                signature = []

                for symbol in alphabet:

                    destination = transition[state][symbol]

                    group_index = next(
                        i for i, p in enumerate(partitions)
                        if destination in p
                    )

                    signature.append(group_index)

                signature = tuple(signature)

                if signature not in groups:
                    groups[signature] = []

                groups[signature].append(state)


            split_groups = list(groups.values())

            if len(split_groups) > 1:
                changed = True

            new_partitions.extend(split_groups)


        partitions = new_partitions


    # -----------------------------
    # Create minimized DFA
    # -----------------------------

    minimized_states = [
        f"Q{i}"
        for i in range(len(partitions))
    ]

    minimized_transitions = []

    for index, group in enumerate(partitions):

        representative = group[0]

        for symbol in alphabet:

            destination = transition[
                representative
            ][symbol]

            destination_group = next(
                i for i, p in enumerate(partitions)
                if destination in p
            )

            minimized_transitions.append({
                "from": f"Q{index}",
                "symbol": symbol,
                "to": f"Q{destination_group}"
            })


    # -----------------------------
    # Start state
    # -----------------------------

    start_group = next(
        i for i, p in enumerate(partitions)
        if start in p
    )

    minimized_start = f"Q{start_group}"


    # -----------------------------
    # Final states
    # -----------------------------

    minimized_final = []

    for index, group in enumerate(partitions):

        if any(
            state in final_set
            for state in group
        ):
            minimized_final.append(
                f"Q{index}"
            )


    # -----------------------------
    # Result
    # -----------------------------

    return {

        "original_states": states,

        "reachable_states":
            reachable_states,

        "removed_states": [
            state for state in states
            if state not in reachable
        ],

        "equivalent_groups": [
            {
                "name": f"Q{i}",
                "states": group
            }
            for i, group in enumerate(partitions)
        ],

        "minimized_states":
            minimized_states,

        "start_state":
            minimized_start,

        "final_states":
            minimized_final,

        "transitions":
            minimized_transitions
    }


# -----------------------------
# Home page
# -----------------------------

@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# Minimize API
# -----------------------------

@app.route("/minimize", methods=["POST"])
def minimize():

    try:

        data = request.get_json()

        states = data["states"]
        alphabet = data["alphabet"]
        start = data["start"]
        final_states = data["final_states"]
        transitions = data["transitions"]

        result = minimize_dfa(
            states,
            alphabet,
            start,
            final_states,
            transitions
        )

        return jsonify({
            "success": True,
            "result": result
        })


    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
